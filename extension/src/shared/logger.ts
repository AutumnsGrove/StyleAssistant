/**
 * Debug logging utility for GroveAssistant extension.
 *
 * Provides structured logging that can be sent to the backend
 * for persistent storage and debugging.
 */

import { getSettings } from "./storage";

export type LogLevel = "info" | "warning" | "error";

interface LogEntry {
  level: LogLevel;
  component: string;
  message: string;
  stack_trace?: string;
}

// Queue for batching log entries
const logQueue: LogEntry[] = [];
let flushTimeout: ReturnType<typeof setTimeout> | null = null;
const FLUSH_INTERVAL = 5000; // 5 seconds
const MAX_QUEUE_SIZE = 20;

/**
 * Logger class for consistent logging across extension components.
 */
export class Logger {
  private component: string;
  private enableRemote: boolean;

  constructor(component: string, enableRemote = true) {
    this.component = component;
    this.enableRemote = enableRemote;
  }

  /**
   * Log an info message.
   */
  info(message: string, data?: unknown): void {
    this.log("info", message, data);
  }

  /**
   * Log a warning message.
   */
  warn(message: string, data?: unknown): void {
    this.log("warning", message, data);
  }

  /**
   * Log an error message.
   */
  error(message: string, error?: Error | unknown): void {
    let stackTrace: string | undefined;

    if (error instanceof Error) {
      stackTrace = error.stack;
      message = `${message}: ${error.message}`;
    } else if (error) {
      message = `${message}: ${String(error)}`;
    }

    this.log("error", message, undefined, stackTrace);
  }

  /**
   * Internal logging method.
   */
  private log(level: LogLevel, message: string, data?: unknown, stackTrace?: string): void {
    const prefix = `[GroveAssistant:${this.component}]`;
    const fullMessage = data ? `${message} ${JSON.stringify(data)}` : message;

    // Always log to console
    switch (level) {
      case "info":
        console.log(prefix, fullMessage);
        break;
      case "warning":
        console.warn(prefix, fullMessage);
        break;
      case "error":
        console.error(prefix, fullMessage);
        if (stackTrace) {
          console.error(stackTrace);
        }
        break;
    }

    // Queue for remote logging (only warnings and errors by default)
    if (this.enableRemote && (level === "warning" || level === "error")) {
      queueLogEntry({
        level,
        component: this.component,
        message: fullMessage,
        stack_trace: stackTrace,
      });
    }
  }
}

/**
 * Queue a log entry for sending to the backend.
 */
function queueLogEntry(entry: LogEntry): void {
  logQueue.push(entry);

  // Flush immediately if queue is full
  if (logQueue.length >= MAX_QUEUE_SIZE) {
    flushLogs();
    return;
  }

  // Schedule flush if not already scheduled
  if (!flushTimeout) {
    flushTimeout = setTimeout(flushLogs, FLUSH_INTERVAL);
  }
}

/**
 * Flush queued log entries to the backend.
 */
async function flushLogs(): Promise<void> {
  if (flushTimeout) {
    clearTimeout(flushTimeout);
    flushTimeout = null;
  }

  if (logQueue.length === 0) {
    return;
  }

  // Take all entries from queue
  const entries = logQueue.splice(0, logQueue.length);

  try {
    const settings = await getSettings();
    const baseUrl = settings.apiEndpoint;

    // Send each log entry (could batch in future)
    for (const entry of entries) {
      try {
        await fetch(`${baseUrl}/api/debug/log`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(entry),
        });
      } catch (error) {
        // Silent fail for individual entries - don't want logging to cause issues
        console.debug("[Logger] Failed to send log entry:", error);
      }
    }
  } catch (error) {
    // Put entries back in queue if flush completely fails
    logQueue.unshift(...entries);
    console.debug("[Logger] Failed to flush logs:", error);
  }
}

/**
 * Force flush all pending logs.
 * Call this before extension unload or when needed.
 */
export async function forceFlushLogs(): Promise<void> {
  await flushLogs();
}

/**
 * Create a logger for a specific component.
 */
export function createLogger(component: string, enableRemote = true): Logger {
  return new Logger(component, enableRemote);
}

// Default loggers for common components
export const contentLogger = createLogger("content_script");
export const backgroundLogger = createLogger("background");
export const popupLogger = createLogger("popup");
export const quizLogger = createLogger("quiz");
