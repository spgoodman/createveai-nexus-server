/**
 * Export all node and credential definitions in a way that works with n8n
 */
import { CreateveAI } from './nodes/CreateveAI.node';
import { CreateveAIApi } from './credentials/CreateveAIApi.credentials';
export declare const nodeTypes: {
    CreateveAI: typeof CreateveAI;
};
export declare const credentialTypes: {
    CreateveAIApi: typeof CreateveAIApi;
};
