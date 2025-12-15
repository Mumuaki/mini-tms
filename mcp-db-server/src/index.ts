#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { knex } from "knex";

// Get database configuration from environment variables
const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  throw new Error('DATABASE_URL environment variable is required');
}

// Configure Knex for PostgreSQL
const db = knex({
  client: 'pg',
 connection: DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"), // Fixed: replace only takes 2 arguments
  searchPath: ['public'],
  pool: {
    min: 2,
    max: 10
  },
  migrations: {
    tableName: 'knex_migrations'
  }
});

// Create an MCP server
const server = new McpServer({
  name: "tms-db-server",
  version: "1.0"
});

// Tool to get all freights from the database
server.tool(
  "get_all_freights",
 {
    limit: z.number().min(1).max(10).optional().describe("Number of records to return (default: 10)"),
    offset: z.number().optional().describe("Offset for pagination (default: 0)"),
    include_hidden: z.boolean().optional().describe("Include hidden freights (default: false)")
  },
  async (params: { limit?: number; offset?: number; include_hidden?: boolean }) => {
    const { limit = 10, offset = 0, include_hidden = false } = params;
    try {
      let query = db('freights');
      
      if (!include_hidden) {
        query = query.where('is_hidden', false);
      }
      
      const freights = await query
        .orderBy('created_at', 'desc')
        .limit(limit)
        .offset(offset);
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(freights, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `Database error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
 }
);

// Tool to get a specific freight by ID
server.tool(
  "get_freight_by_id",
  {
    id: z.number().int().positive().describe("Freight ID")
  },
  async (params: { id: number }) => {
    const { id } = params;
    try {
      const freight = await db('freights').where('id', id).first();
      
      if (!freight) {
        return {
          content: [
            {
              type: "text",
              text: `Freight with ID ${id} not found`,
            },
          ],
          isError: true,
        };
      }
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(freight, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `Database error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
 }
);

// Start receiving messages on stdin and sending messages on stdout
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('TMS Database MCP server running on stdio');