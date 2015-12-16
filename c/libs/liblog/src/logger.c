/*
 * @file   logger.c
 * @author Tony Persson (tony.persson@rubico.com)
 * 
 * Stub for liblog...
 *
 * Shared library used to log data to log server.
 */

#include <stdio.h>
#include <time.h>
#include "logger.h"

/* log_level variable. */
static int log_level = LOG_INFO;

/*
 * Sets the log level to the specified value.
 * 
 * @param level Can be  LOG_WARNING, LOG_ERROR, LOG_INFO or LOG_DEBUG
 * 
 */
void logger_set_level(int level)
{
	log_level = level;
}

/*
 * Send log data to log server. Just a STUB for the moment...
 *
 * @param file     Name of file for DEV-logging (set by macro).
 * @param line     Line number for DEV-logging (set by macro).
 * @param loglevel Level of log message.
 * @param format   Log message formating.
 * @param ...      Arguments sent in format-string.
 */
void logger(const char *file, const int line, int level, const char *format, ...)
{
    // STUB STUB STUB!!!

    va_list args;
    char   time_str[20];
    time_t rawtime;
    struct tm * timeinfo;


    if(log_level < level)
	return;


    rawtime = time(NULL);
    timeinfo = localtime(&rawtime);
    strftime (time_str, 20, "%F %X", timeinfo);

    printf("%s: ", time_str);

    /* Log type */
    switch(level)
    {
    case LOG_INFO:
	printf("INFO: ");
	break;

    case LOG_WARNING:
	printf("WARNING: ");
	break;

    case LOG_ERROR:
	printf("ERROR: ");
	break;

    case LOG_DEBUG:
	printf("DEBUG: ");
	break;

    case LOG_DEV:
	printf("DEV: ");
	break;

    default:
	break;
    }

    /* Debug data for DEBUG */
    if(log_level >= LOG_DEBUG)
    {
	printf("(%s:%d): ", file, line);
    }

    va_start (args, format);
    vprintf(format, args);
    va_end(args);

    printf("\n");
}
