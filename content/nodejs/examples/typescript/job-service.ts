export type JobState = 'queued' | 'processing' | 'completed' | 'failed';
export interface Job { id: string; ownerId: string; state: JobState }
export interface JobRepository { find(id: string): Promise<Job | null> }
export class JobService {
  constructor(private readonly repository: JobRepository) {}
  async ownedJob(id: string, userId: string): Promise<Job | null> {
    const job = await this.repository.find(id);
    return job?.ownerId === userId ? job : null;
  }
}
