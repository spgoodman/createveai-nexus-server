import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { Config } from "./config.js";

/**
 * Client for interacting with the Createve.AI Nexus REST API
 */
export class NexusClient {
  private client: AxiosInstance;
  private apiFilter?: string;
  private debug: boolean;

  /**
   * Create a new Nexus API client
   */
  constructor(config: Config) {
    this.apiFilter = config.api;
    this.debug = config.debug;

    // Create Axios instance with authentication
    this.client = axios.create({
      baseURL: config.baseUrl,
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        "Content-Type": "application/json",
      },
    });

    // Add request/response logging for debug mode
    if (this.debug) {
      this.setupDebugInterceptors();
    }
  }

  /**
   * Get the OpenAPI schema from the server
   */
  async getSchema(): Promise<any> {
    try {
      // If API filter is specified, get schema for that API only
      const endpoint = this.apiFilter 
        ? `/openapi/${this.apiFilter}.json` 
        : "/openapi.json";

      const response = await this.client.get(endpoint);
      return response.data;
    } catch (error) {
      this.handleApiError("Error fetching OpenAPI schema", error);
      throw error;
    }
  }

  /**
   * Execute an API endpoint with the provided parameters
   */
  async executeApi(apiPath: string, params: any): Promise<any> {
    try {
      const endpoint = `/api/${apiPath}`;
      const response = await this.client.post(endpoint, params);
      return response.data;
    } catch (error) {
      this.handleApiError(`Error executing API ${apiPath}`, error);
      throw error;
    }
  }

  /**
   * Get the status of a queued request
   */
  async getQueueStatus(queueId: string): Promise<any> {
    try {
      const response = await this.client.get(`/queue/${queueId}`);
      return response.data;
    } catch (error) {
      this.handleApiError(`Error getting queue status for ${queueId}`, error);
      throw error;
    }
  }

  /**
   * Get documentation from the server
   */
  async getDocumentation(path?: string): Promise<string> {
    try {
      const endpoint = path ? `/docs/${path}` : "/docs";
      const response = await this.client.get(endpoint);
      return response.data;
    } catch (error) {
      this.handleApiError("Error fetching documentation", error);
      throw error;
    }
  }

  /**
   * Set up debug interceptors for logging requests and responses
   */
  private setupDebugInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.error(`[DEBUG] Request: ${config.method?.toUpperCase()} ${config.url}`);
        if (config.data) {
          console.error(`[DEBUG] Request Body:`, JSON.stringify(config.data, null, 2));
        }
        return config;
      },
      (error) => {
        console.error(`[DEBUG] Request Error:`, error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.error(`[DEBUG] Response: ${response.status} ${response.statusText}`);
        console.error(`[DEBUG] Response Data:`, JSON.stringify(response.data, null, 2));
        return response;
      },
      (error) => {
        console.error(`[DEBUG] Response Error:`, error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Handle API errors in a consistent way
   */
  private handleApiError(context: string, error: any): void {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const message = error.response?.data?.message || error.message;
      
      if (status === 401) {
        console.error(`Authentication error: Invalid API key or permissions`);
      } else if (status === 404) {
        console.error(`Resource not found: ${error.config?.url}`);
      } else {
        console.error(`${context}: ${message}`);
      }

      if (this.debug && error.response?.data) {
        console.error("Response details:", error.response.data);
      }
    } else {
      console.error(`${context}: ${error.message || error}`);
    }
  }
}
