import { IDataObject, INodeExecutionData } from 'n8n-workflow';
/**
 * Convert binary data to base64 for API input
 */
export declare function handleBinaryInputData(parameters: IDataObject, item: INodeExecutionData): void;
/**
 * Process API response and convert binary data fields to n8n binary data
 */
export declare function processBinaryOutputData(response: IDataObject, item: INodeExecutionData, executionId: string): INodeExecutionData;
