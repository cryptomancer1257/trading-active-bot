/**
 * Utility functions for handling variable injection in prompt templates
 */

export interface PromptVariables {
  formatted_timeframes?: string;
  current_price?: number;
  symbol?: string;
  exchange?: string;
  timeframe?: string;
  [key: string]: any;
}

/**
 * Available variables that can be used in prompt templates
 */
export const AVAILABLE_VARIABLES = {
  formatted_timeframes: {
    description: "Formatted timeframes for analysis (e.g., '1h, 4h, 1d')",
    example: "{formatted_timeframes}",
    type: "string"
  },
  current_price: {
    description: "Current price of the trading pair",
    example: "{current_price}",
    type: "number"
  },
  symbol: {
    description: "Trading symbol (e.g., 'BTC/USDT')",
    example: "{symbol}",
    type: "string"
  },
  exchange: {
    description: "Exchange name (e.g., 'Binance')",
    example: "{exchange}",
    type: "string"
  },
  timeframe: {
    description: "Primary timeframe for analysis",
    example: "{timeframe}",
    type: "string"
  },
  timestamp: {
    description: "Current timestamp",
    example: "{timestamp}",
    type: "string"
  },
  user_id: {
    description: "User ID",
    example: "{user_id}",
    type: "number"
  },
  bot_id: {
    description: "Bot ID",
    example: "{bot_id}",
    type: "number"
  }
} as const;

/**
 * Extract all variables from a prompt template
 */
export function extractVariables(template: string): string[] {
  const variableRegex = /\{([^}]+)\}/g;
  const variables: string[] = [];
  let match;
  
  while ((match = variableRegex.exec(template)) !== null) {
    variables.push(match[1]);
  }
  
  return Array.from(new Set(variables)); // Remove duplicates
}

/**
 * Replace variables in a prompt template with actual values
 */
export function injectVariables(template: string, variables: PromptVariables): string {
  let result = template;
  
  // Replace all variables with their values
  Object.entries(variables).forEach(([key, value]) => {
    const regex = new RegExp(`\\{${key}\\}`, 'g');
    result = result.replace(regex, String(value));
  });
  
  // Replace any remaining variables with empty string or placeholder
  const remainingVariables = extractVariables(result);
  remainingVariables.forEach(variable => {
    const regex = new RegExp(`\\{${variable}\\}`, 'g');
    result = result.replace(regex, `{${variable}}`); // Keep original if no value provided
  });
  
  return result;
}

/**
 * Validate that all variables in a template are supported
 */
export function validateVariables(template: string): { valid: boolean; errors: string[] } {
  const variables = extractVariables(template);
  const supportedVariables = Object.keys(AVAILABLE_VARIABLES);
  const errors: string[] = [];
  
  variables.forEach(variable => {
    if (!supportedVariables.includes(variable)) {
      errors.push(`Unsupported variable: {${variable}}`);
    }
  });
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Get default values for common variables
 */
export function getDefaultVariables(): PromptVariables {
  return {
    formatted_timeframes: "1h, 4h, 1d",
    current_price: 0,
    symbol: "BTC/USDT",
    exchange: "Binance",
    timeframe: "1h",
    timestamp: new Date().toISOString(),
    user_id: 0,
    bot_id: 0
  };
}
