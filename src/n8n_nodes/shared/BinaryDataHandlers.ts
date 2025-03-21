import {
	IBinaryData,
	IBinaryKeyData,
	IDataObject,
	INodeExecutionData,
	NodeOperationError,
	INode,
} from 'n8n-workflow';

/**
 * Check if data is base64 encoded
 */
function isBase64(str: string): boolean {
	try {
		return Buffer.from(str, 'base64').toString('base64') === str;
	} catch (error) {
		return false;
	}
}

/**
 * Extract mime type from data URL
 */
function getMimeTypeFromDataUrl(dataUrl: string): string {
	if (!dataUrl.startsWith('data:')) return 'application/octet-stream';
	
	const matches = dataUrl.match(/^data:([^;]+);base64,/);
	return matches ? matches[1] : 'application/octet-stream';
}

/**
 * Convert binary data to base64 for API input
 */
export function handleBinaryInputData(
	parameters: IDataObject,
	item: INodeExecutionData,
): void {
	// Process each parameter
	for (const key of Object.keys(parameters)) {
		if (parameters[key] === '={{ $binary }}') {
			// Remove the placeholder
			delete parameters[key];
			
			// Check if we have binary data - safeguarded version
			if (item.binary === undefined) {
				console.error(`No binary data found for parameter "${key}"`);
				return;
			}
			
			// Find first available binary property
			const binaryPropertyName = Object.keys(item.binary)[0];
			if (!binaryPropertyName) {
				console.error(`No binary property found for parameter "${key}"`);
				return;
			}
			
			// Get binary data
			const binaryData = item.binary[binaryPropertyName];
			if (!binaryData) {
				console.error(`Binary data is empty for parameter "${key}"`);
				return;
			}
			
			// Set the base64 data
			parameters[key] = binaryData.data;
		}
	}
}

/**
 * Process API response and convert binary data fields to n8n binary data
 */
export function processBinaryOutputData(
	response: IDataObject,
	item: INodeExecutionData,
	executionId: string,
): INodeExecutionData {
	const returnItem: INodeExecutionData = { ...item, json: response };
	const binaryData: IBinaryKeyData = {}; // Use IBinaryKeyData instead

	// Check for binary data in response
	for (const [key, value] of Object.entries(response)) {
		// Skip if not a string or not a potential binary/base64 field
		if (typeof value !== 'string') continue;
		
		const trimmedValue = (value as string).trim();
		
		// Check if this is a data URL
		if (trimmedValue.startsWith('data:')) {
			try {
				// Extract the base64 part
				const base64Data = trimmedValue.split(',')[1] || '';
				if (!base64Data) continue;
				
				// Get the mime type
				const mimeType = getMimeTypeFromDataUrl(trimmedValue);
				
				// Create file extension from mime type
				const fileExtension = mimeType.split('/')[1] || 'dat';
				
				// Create binary data entry
				binaryData[key] = {
					data: base64Data,
					mimeType,
					fileName: `${key}.${fileExtension}`,
					fileExtension,
				};
			} catch (error) {
				// Skip if we can't process
				continue;
			}
		}
		// Check if this might be raw base64 data
		else if (isBase64(trimmedValue) && trimmedValue.length > 100) {
			// Since we don't know the mime type, use generic binary
			binaryData[key] = {
				data: trimmedValue,
				mimeType: 'application/octet-stream',
				fileName: `${key}.bin`,
				fileExtension: 'bin',
			};
		}
	}
	
	// If we found binary data, add it to the item
	if (Object.keys(binaryData).length > 0) {
		returnItem.binary = binaryData;
	}
	
	return returnItem;
}
