/*
 * @file   logger.c
 * @author Tony Persson (tony.persson@rubico.com)
 * 
 * Stub for liblog...
 *
 * Shared library used to log data to log server.
 */

#ifndef _LOGGING_H_
#define _LOGGING_H_


#include <stdarg.h>

/* Strings */
#define LOG_LEVEL_INFO_STR  "INFO"   /**< Possible value for -l argument */
#define LOG_LEVEL_DEBUG_STR "DEBUG"  /**< Possible value for -l argument */
#define LOG_LEVEL_DEV_STR   "DEV"    /**< Possible value for -l argument */

/* Possible levels of logging */
#define LOG_WARNING 0   /**< Log level: WARNING: Bad stuff has happened. */
#define LOG_ERROR   1   /**< Log level: ERROR:   Very bad stuff has happended */
#define LOG_INFO    5   /**< Log level: INFO:    Normal system info */
#define LOG_DEBUG   10  /**< Log level: DEBUG    Packet/segment debugging */
#define LOG_DEV     100 /**< Log level: DEV:     Developer logging */

/* Default log level */
#define LOG_DEFAULT LOG_INFO

/* Meta info for DEV-log macro */
#define LOG_META __FILE__, __LINE__

/* Short macro for LOG_WARNING */
#define WARN(format, ...) logger(LOG_META, LOG_WARNING, format, ##__VA_ARGS__)

/* Short macro for LOG_ERROR */
#define ERR(format, ...) logger(LOG_META, LOG_ERROR, format, ##__VA_ARGS__)

/* Short macro for LOG_NORMAL */
#define LOG(format, ...) logger(LOG_META, LOG_INFO, format, ##__VA_ARGS__)

/* Short macro for LOG_DEBUG */
#define DBG(format, ...) logger(LOG_META, LOG_DEBUG, format, ##__VA_ARGS__)

/* Short macro for LOG_DEV */
#define DEV(format, ...) logger(LOG_META, LOG_DEV, format, ##__VA_ARGS__)

/* External function prototypes */
void logger(const char *file, const int line, int level, const char *format, ...);
void logger_set_level(int level);

#endif
