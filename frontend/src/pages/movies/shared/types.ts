export interface Movie {
	id: number;
	title: string;
	release_date: string;
	vote_average: number;
	poster_path: string | null;
	backdrop_path: string | null;
	overview: string;
}

export interface MovieCardProps {
	movie: Movie;
}

export type DownloadStatus = 'PENDING' | 'DOWNLOADING' | 'CONVERTING' | 'READY' | 'ERROR';

export interface MoviePlayerProps {
	movieId: string;
}