import logging

# Define the logging configuration dictionary
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,  # Optional, avoid overriding existing loggers
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',  # Adjust logging level as needed
            'formatter': 'standard'
        },
        # Optional file handler (add more handlers as needed)
        'file': {
            'class': 'logging.FileHandler',
            'level': 'WARNING',  # Adjust level for file logging
            'filename': 'my_app.log',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console'],
            'level': 'INFO',  # Adjust root logger level if needed
            'propagate': True  # Propagate messages to parent loggers
        }
    }
}