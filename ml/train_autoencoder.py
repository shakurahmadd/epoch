import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset

from lstm_autoencoder import LSTMAutoencoder


SEQUENCES_DIR = Path(__file__).parent / "data" / "sequences"
MODELS_DIR = Path(__file__).parent / "models"

SEQ_LEN = 90
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3
THRESHOLD_PERCENTILE = 95


def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for batch in dataloader:
        x = batch[0].to(device)
        optimizer.zero_grad()
        x_hat = model(x)
        loss = criterion(x_hat, x)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)


def compute_threshold(model, dataloader, device):
    model.eval()
    errors = []
    with torch.no_grad():
        for batch in dataloader:
            x = batch[0].to(device)
            x_hat = model(x)
            mse = ((x_hat - x) ** 2).mean(dim=(1, 2))
            errors.extend(mse.cpu().tolist())
    return float(np.percentile(errors, THRESHOLD_PERCENTILE))


def main():
    MODELS_DIR.mkdir(exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    station_ids = sorted(set(
        f.stem.split("_")[1] for f in SEQUENCES_DIR.glob("station_*_*.npy")
    ))
    print(f"Training on {len(station_ids)} stations (device: {device})")

    for i, station_id in enumerate(station_ids):
        arrays = [
            np.load(SEQUENCES_DIR / f"station_{station_id}_{season}.npy")
            for season in ("winter", "spring", "summer", "autumn")
            if (SEQUENCES_DIR / f"station_{station_id}_{season}.npy").exists()
        ]
        if not arrays:
            continue

        data = np.concatenate(arrays, axis=0)  # [N, 90, 3]
        dataset = TensorDataset(torch.tensor(data))
        dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

        model = LSTMAutoencoder(seq_len=SEQ_LEN).to(device)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

        print(f"[{i+1}/{len(station_ids)}] Station {station_id} — {len(data)} windows")
        for epoch in range(EPOCHS):
            loss = train_epoch(model, dataloader, optimizer, criterion, device)
            if (epoch + 1) % 10 == 0:
                print(f"  epoch {epoch+1}/{EPOCHS} loss: {loss:.6f}")

        threshold = compute_threshold(model, dataloader, device)
        torch.save({"model_state": model.state_dict(), "threshold": threshold},
                   MODELS_DIR / f"station_{station_id}.pt")
        print(f"  threshold: {threshold:.6f} — saved")

    print("Done.")


if __name__ == "__main__":
    main()
