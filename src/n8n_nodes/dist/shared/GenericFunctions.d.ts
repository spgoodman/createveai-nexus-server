import { IExecuteFunctions, IHookFunctions, ILoadOptionsFunctions } from 'n8n-workflow';
import { AxiosInstance } from 'axios';
import { IDataObject } from 'n8n-workflow';
/**
 * Create an Axios instance with authentication
 */
export declare function getApiClient(this: IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions, baseUrl: string, apiKey: string): AxiosInstance;
/**
 * Execute an API request to the Createve.AI API
 */
export declare function executeApiRequest(this: IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions, apiUrl: string, apiKey: string, endpoint: string, parameters: IDataObject): Promise<IDataObject>;
/**
 * Poll queue status until complete
 */
export declare function pollQueueStatus(this: IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions, apiUrl: string, apiKey: string, endpoint: string, queueId: string, maxPollTime?: number, pollInterval?: number): Promise<IDataObject>;
