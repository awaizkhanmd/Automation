  
automation/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── database.py
│   └── job_sites.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── connection.py
│   └── migrations/
│       ├── __init__.py
│       └── 001_initial_schema.sql
├── src/
│   ├── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── automation/
│   │   └── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── helpers.py
│   │   └── validators.py
│   └── dashboard/
│       └── __init__.py
├── data/
│   ├── profiles/
│   ├── resumes/
│   └── logs/
├── tests/
│   ├── __init__.py
│   ├── test_automation/
│   ├── test_core/
│   └── test_utils/
├── scripts/
│   ├── setup_database.py
│   └── view_stats.py
└── docs/
    ├── SETUP.md
    ├── USAGE.md
    └── API.md