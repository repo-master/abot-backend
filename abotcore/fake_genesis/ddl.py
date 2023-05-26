
from sqlalchemy import event, DDL


def create_ddl(target, connection, **kwargs):
    fn_update_sensor_status = DDL("""
    CREATE OR REPLACE FUNCTION update_sensor_status()
        RETURNS int4
        AS $$
    	BEGIN
            RETURN 0;
	    END;
        $$ LANGUAGE plpgsql
    """).execute_if(dialect='postgresql')

    trig_update_sensor_status = DDL("""
    CREATE TRIGGER trig_update_sensor_status
    AFTER INSERT OR UPDATE ON genesis.sensor_data
    EXECUTE PROCEDURE update_sensor_status()
    """).execute_if(dialect='postgresql')

    #fn_update_sensor_status(target, connection, **kwargs)
    #trig_update_sensor_status(target, connection, **kwargs)

def register_post_relation_handlers(base_model):
    event.listen(base_model.metadata, 'after_create', create_ddl)
