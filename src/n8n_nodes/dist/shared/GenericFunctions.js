"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.pollQueueStatus = exports.executeApiRequest = exports.getApiClient = void 0;
const axios_1 = __importDefault(require("axios"));
/**
 * Create an Axios instance with authentication
 */
function getApiClient(baseUrl, apiKey) {
    const client = axios_1.default.create({
        baseURL: baseUrl,
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    });
    // Handle errors (simplified)
    client.interceptors.response.use((response) => response, (error) => {
        // Just rethrow the basic error to avoid type issues
        throw error;
    });
    return client;
}
exports.getApiClient = getApiClient;
/**
 * Execute an API request to the Createve.AI API
 */
async function executeApiRequest(apiUrl, apiKey, endpoint, parameters) {
    const client = getApiClient.call(this, apiUrl, apiKey);
    try {
        // Make request to the Createve.AI API
        const response = await client.post(`/api/${endpoint}`, parameters);
        return response.data;
    }
    catch (error) {
        // Simplified error handling
        throw new Error(`API Request Error: ${error.message}`);
    }
}
exports.executeApiRequest = executeApiRequest;
/**
 * Poll queue status until complete
 */
async function pollQueueStatus(apiUrl, apiKey, endpoint, queueId, maxPollTime = 300, pollInterval = 2) {
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
                return response.data;
            }
            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
        }
        catch (error) {
            // Simplified error handling
            throw new Error(`Queue polling error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    // If we get here, we've timed out
    throw new Error(`Polling timed out after ${maxPollTime} seconds`);
}
exports.pollQueueStatus = pollQueueStatus;
//# sourceMappingURL=GenericFunctions.js.map