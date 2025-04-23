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
	PENDING = "PENDING",
	DOWNLOADING = "DOWNLOADING",
	READY = "READY",
	ERROR = "ERROR",
	CONVERTING = "CONVERTING"
}

export interface MoviePlayerProps {
	movieId: string;
	magnet: string;
}

export interface MovieStatusResponse {
	status: DownloadStatus;
	progress: number;
	file_path?: string;
	message?: string;
	error?: string;
}