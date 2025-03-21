/**
 * Export all node and credential definitions in a way that works with n8n
 */
// The actual node and credential classes
import { CreateveAI } from './nodes/CreateveAI.node';
import { CreateveAIApi } from './credentials/CreateveAIApi.credentials';

// Exports for n8n to discover the nodes and credentials
export const nodeTypes = {
  CreateveAI,
};

export const credentialTypes = {
  CreateveAIApi,
};
