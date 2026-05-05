import axios from 'axios'
import type {NarrativeResponse, TimelineResponse} from '../types/climate'


export async function fetchTimeline(
    postcode: string,
    birthYear: number
): Promise<TimelineResponse> {
    const { data } = await axios.get<TimelineResponse>(
        `/api/climate/timeline/${postcode}/${birthYear}`
    )
    return data
}



export async function fetchNarrative(
    birthYear: number,
    region: string,
    postcode: string
): Promise<NarrativeResponse> {
    const { data } = await axios.post<NarrativeResponse>('/api/narrative', {
        birth_year: birthYear,
        region: region,
        postcode: postcode
    })
    return data
}