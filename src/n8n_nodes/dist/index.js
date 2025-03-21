"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.credentialTypes = exports.nodeTypes = void 0;
/**
 * Export all node and credential definitions in a way that works with n8n
 */
// The actual node and credential classes
const CreateveAI_node_1 = require("./nodes/CreateveAI.node");
const CreateveAIApi_credentials_1 = require("./credentials/CreateveAIApi.credentials");
// Exports for n8n to discover the nodes and credentials
exports.nodeTypes = {
    CreateveAI: CreateveAI_node_1.CreateveAI,
};
exports.credentialTypes = {
    CreateveAIApi: CreateveAIApi_credentials_1.CreateveAIApi,
};
//# sourceMappingURL=index.js.map