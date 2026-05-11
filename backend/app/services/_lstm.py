import torch
import torch.nn as nn


class Encoder(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, latent_size=32):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden_size, latent_size, batch_first=True)

    def forward(self, x):
        out, _ = self.lstm1(x)
        _, (h_n, _) = self.lstm2(out)
        return h_n[-1]


class Decoder(nn.Module):
    def __init__(self, latent_size=32, hidden_size=64, output_size=3, seq_len=90):
        super().__init__()
        self.seq_len = seq_len
        self.lstm1 = nn.LSTM(latent_size, hidden_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden_size, hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, output_size)

    def forward(self, z):
        z = z.unsqueeze(1).repeat(1, self.seq_len, 1)
        out, _ = self.lstm1(z)
        out, _ = self.lstm2(out)
        return self.linear(out)


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, latent_size=32, seq_len=90):
        super().__init__()
        self.encoder = Encoder(input_size, hidden_size, latent_size)
        self.decoder = Decoder(latent_size, hidden_size, input_size, seq_len)

    def forward(self, x):
        return self.decoder(self.encoder(x))
