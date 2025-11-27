CREATE DATABASE "url_shortner" ;

CREATE USER "url_shortner_user" WITH PASSWORD 'sdjnnfejsajad3574nndfkd' ;

ALTER ROLE "url_shortner_user" SET client_encoding TO 'utf8' ;

ALTER ROLE "url_shortner_user" SET default_transaction_isolation TO 'read committed' ;

ALTER ROLE "url_shortner_user" SET timezone TO 'UTC' ;

ALTER USER "url_shortner_user" CREATEDB ;

GRANT ALL PRIVILEGES ON DATABASE url_shortner TO "url_shortner_user" ;

GRANT ALL ON schema public TO "url_shortner_user" ;

SELECT has_schema_privilege( 'url_shortner_user','public','CREATE') ;

ALTER DATABASE "url_shortner" OWNER TO "url_shortner_user" ;
