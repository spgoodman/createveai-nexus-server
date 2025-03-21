import { Config } from "./config.js";
/**
 * Client for interacting with the Createve.AI Nexus REST API
 */
export declare class NexusClient {
    private client;
    private apiFilter?;
    private debug;
    /**
     * Create a new Nexus API client
     */
    constructor(config: Config);
    /**
     * Get the OpenAPI schema from the server
     */
    getSchema(): Promise<any>;
    /**
     * Execute an API endpoint with the provided parameters
     */
    executeApi(apiPath: string, params: any): Promise<any>;
    /**
     * Get the status of a queued request
     */
    getQueueStatus(queueId: string): Promise<any>;
    /**
     * Get documentation from the server
     */
    getDocumentation(path?: string): Promise<string>;
    /**
     * Set up debug interceptors for logging requests and responses
     */
    private setupDebugInterceptors;
    /**
     * Handle API errors in a consistent way
     */
    private handleApiError;
}
