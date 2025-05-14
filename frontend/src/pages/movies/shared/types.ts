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

export enum DownloadStatus {
	NOT_STARTED = 'NOT_STARTED',
	DOWNLOADING = 'DOWNLOADING',
	CONVERTING = 'CONVERTING',
	READY = 'READY',
	ERROR = 'ERROR'
}

export interface MoviePlayerProps {
	movieId: number;
	magnet: string;
}

export interface MovieStatusResponse {
	status: DownloadStatus;
	progress?: number;
	movie_file_id?: string;
	error?: string;
}