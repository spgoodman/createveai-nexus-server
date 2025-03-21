import {
	IExecuteFunctions,
	IHookFunctions,
	ILoadOptionsFunctions,
	NodeApiError,
	INode,
	JsonObject,
} from 'n8n-workflow';
import axios, { AxiosInstance, AxiosError } from 'axios';
import { IDataObject } from 'n8n-workflow';

/**
 * Create an Axios instance with authentication
 */
export function getApiClient(
	this: IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions,
	baseUrl: string,
	apiKey: string,
): AxiosInstance {
	const client = axios.create({
		baseURL: baseUrl,
		headers: {
			'Authorization': `Bearer ${apiKey}`,
			'Content-Type': 'application/json',
			'Accept': 'application/json',
		},
	});

		// Handle errors (simplified)
		client.interceptors.response.use(
			(response) => response,
			(error) => {
				// Just rethrow the basic error to avoid type issues
				throw error;
			},
		);

	return client;
}

/**
 * Execute an API request to the Createve.AI API
 */
export async function executeApiRequest(
	this: IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions,
	apiUrl: string,
	apiKey: string,
	endpoint: string,
	parameters: IDataObject,
): Promise<IDataObject> {
	const client = getApiClient.call(this, apiUrl, apiKey);

	try {
		// Make request to the Createve.AI API
		const response = await client.post(`/api/${endpoint}`, parameters);
		return response.data as IDataObject;
	} catch (error: any) {
		// Simplified error handling
		throw new Error(`API Request Error: ${error.message}`);
	}
}

/**
 * Poll queue status until complete
 */
export async function pollQueueStatus(
	this: IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions,
	apiUrl: string,
	apiKey: string,
	endpoint: string,
	queueId: string,
	maxPollTime: number = 300,
	pollInterval: number = 2,
): Promise<IDataObject> {
	const client = getApiClient.call(this, apiUrl, apiKey);
	const queueEndpoint = `/api/${endpoint}/queue`;
	
	// Calculate max attempts
	const maxAttempts = Math.ceil(maxPollTime / pollInterval);
	let attempts = 0;

	// Poll until complete or timeout
	while (attempts < maxAttempts) {
		attempts++;
		
		try {
			const response = await client.post(queueEndpoint, { queue_id: queueId });
			
			// If the response doesn't contain a queue_id, the job is complete
			if (!response.data.queue_id) {
				return response.data as IDataObject;
			}
			
			// Wait before next poll
			await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
		} catch (error) {
			// Simplified error handling
			throw new Error(`Queue polling error: ${error instanceof Error ? error.message : 'Unknown error'}`);
		}
	}

	// If we get here, we've timed out
	throw new Error(`Polling timed out after ${maxPollTime} seconds`);
}
