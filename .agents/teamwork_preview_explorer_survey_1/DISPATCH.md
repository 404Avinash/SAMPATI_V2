## 2026-08-28T18:53:43Z

<USER_REQUEST>
You are Explorer 1 for the SAMPATI V2 upgrade survey.

Your working directory is:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_1\

Project workspace:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2

Original User Request:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\ORIGINAL_REQUEST.md

Your Task:
Read ORIGINAL_REQUEST.md thoroughly. Investigate the backend codebase for Requirement R1 (AWS RDS PostgreSQL Persistence):
1. Locate where all in-memory state is currently stored (cases, mule ring records, analyst feedback, aggregate stats).
2. Detail all schemas / data models needed for PostgreSQL (UPI cases, mule rings, feedback, stats).
3. Investigate how database connection (`DATABASE_URL`), asyncpg/psycopg connection pooling (configured for t3.micro <=87 connections), and automatic table creation on startup should be structured in FastAPI.
4. Check `requirements.txt`, `Dockerfile`, and `deploy/ec2_userdata.sh` and list all changes needed.
5. Check how `/upi/cases`, `/upi/stats`, and `/health` currently work and how they must be updated to query the database.
6. Write a comprehensive survey report to:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_1\survey_backend_persistence.md
and write a standard handoff.md in your working directory.
7. Send a message to parent with the summary and path to your report. Do not modify source code.
</USER_REQUEST>
