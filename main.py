from flask import Flask, render_template, request, redirect, url_for, jsonify
from threading import Thread
import json
import oracledb
import config

secret_key = config.secret_key

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

username = config.username
password = config.password
dsn = config.dsn

pool = oracledb.create_pool(user=username, password=password, dsn=dsn, min=1, max=5, increment=1)

@app.errorhandler(404)
def page_not_found(error):
    return "Page not found", 404

@app.route('/')
def index():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        search_name = request.args.get('search_name')

        if search_name:
            query = "SELECT * FROM TESTS WHERE NAME LIKE '%' || :search_name || '%' ORDER BY NAME"
            cursor.execute(query, {'search_name': search_name})
        else:
            query = "SELECT * FROM TESTS ORDER BY ID DESC"
            cursor.execute(query)

        tests = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            tests.append(dict(zip(column_names, row)))

        cursor.close()
        connection.close()

        return render_template('index.html', tests=tests)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"

@app.route('/add_test', methods=['POST'])
def add_test():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        test_name = request.form['new_test_name']

        query = "INSERT INTO TESTS (ID, NAME) VALUES (TESTS_SEQ.NEXTVAL, :name)"
        cursor.execute(query, {'name': test_name})

        connection.commit()

        cursor.execute("SELECT TESTS_SEQ.CURRVAL FROM dual")
        new_id = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return redirect(url_for('edit_steps', test_id=new_id))

    except oracledb.Error as error:
        return f"Error inserting new test: {error}"



@app.route('/job_details')
def job_details():
    try:
        run_id_filter = request.args.get('run_id')

        connection = pool.acquire()
        cursor = connection.cursor()

        if run_id_filter:
            query = "SELECT * FROM TEST_RUN_LOG WHERE RUN_ID = :run_id ORDER BY EVENT_TIME DESC"
            cursor.execute(query, {'run_id': run_id_filter})
        else:
            query = "SELECT * FROM TEST_RUN_LOG ORDER BY EVENT_TIME DESC"
            cursor.execute(query)

        job_details = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            job_details.append(dict(zip(column_names, row)))

        cursor.close()

        return render_template('job_details.html', job_details=job_details)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"


@app.route('/job_steps_details')
def job_steps_details():
    try:
        run_id_filter = request.args.get('run_id')

        connection = pool.acquire()
        cursor = connection.cursor()

        if run_id_filter:
            query = "SELECT * FROM STEP_RUN_LOG WHERE RUN_ID = :run_id ORDER BY EVENT_TIME DESC"
            cursor.execute(query, {'run_id': run_id_filter})
        else:
            query = "SELECT * FROM STEP_RUN_LOG ORDER BY EVENT_TIME DESC"
            cursor.execute(query)

        job_steps_details = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            job_steps_details.append(dict(zip(column_names, row)))

        cursor.close()

        return render_template('job_steps_details.html', job_steps_details=job_steps_details)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"


        

@app.route('/test_steps/<test_id>')
def test_steps(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = """
        SELECT ts.*, 
               (SELECT srl.OUTPUT_MESSAGE
                FROM STEP_RUN_LOG srl 
                WHERE srl.STEP_ID = ts.ID 
                ORDER BY srl.EVENT_TIME DESC 
                FETCH FIRST ROW ONLY) AS LATEST_OUTPUT,
               (SELECT srl.RUN_ID
                FROM STEP_RUN_LOG srl 
                WHERE srl.STEP_ID = ts.ID 
                ORDER BY srl.EVENT_TIME DESC 
                FETCH FIRST ROW ONLY) AS LATEST_RUN_ID
        FROM TEST_STEPS ts
        WHERE ts.TEST_ID = :test_id
        ORDER BY ts.ORDERNUMBER
        """
        cursor.execute(query, test_id=test_id)

        test_steps_data = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            test_steps_data.append(dict(zip(column_names, row)))

        cursor.close()

        return render_template('test_steps.html', test_id=test_id, test_steps=test_steps_data)
    
    except oracledb.Error as error:
        return f"Error retrieving test steps: {error}"




@app.route('/edit_steps/<test_id>')
def edit_steps(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_STEPS WHERE TEST_ID = :test_id ORDER BY ORDERNUMBER"
        cursor.execute(query, test_id=test_id)
        test_steps_data = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            test_steps_data.append(dict(zip(column_names, row)))

        sql = "SELECT DISTINCT(MODULE) FROM LM.INV_JOBS ORDER BY MODULE ASC"
        cursor.execute(sql)
        modules = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        cursor.close()

        return render_template('edit_steps.html', test_id=test_id, modules=modules, test_steps=test_steps_data)

    except oracledb.Error as error:
        return f"Error retrieving test steps: {error}"


@app.route('/update_order', methods=['POST'])
def update_order():
    data = request.get_json()
    
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        for item in data:
            query = "UPDATE TEST_STEPS SET ORDERNUMBER = :order_number WHERE ID = :id"
            cursor.execute(query, order_number=item['order_number'], id=item['id'])

        connection.commit()
        
        return jsonify({"success": True}), 200

    except Exception as e:
        print(e)
        return jsonify({"success": False}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/add_step/<test_id>', methods=['POST'])
def add_step(test_id):
    try:
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify({'success': False, 'error': 'Invalid input format'})

        new_step_name = data.get('new_step_name')
        step_type = data.get('step_type')
        sql_code = ''
        target_user = ''

        def default_if_none(value, default=''):
            return value if value is not None else default

        target_user = 'LM'
        module = default_if_none(data.get('module'))
        _type = default_if_none(data.get('type'))
        name = default_if_none(data.get('name'))

        sql_code = f"""
        declare 
            p_result varchar2(4000); 
            p_err_code varchar2(4000); 
            p_output clob; 
        begin 
            lm.{_type}.execute(1, '{module}', q'({name})', p_result, p_err_code, p_output, false); 
            dbms_output.put_line(p_result || ' - ' || p_err_code); 
            dbms_output.put_line(p_output); 
        end; 
        """

        connection = pool.acquire()
        cursor = connection.cursor()

        try:
            new_order_query = "SELECT MAX(ORDERNUMBER) FROM TEST_STEPS WHERE TEST_ID = :test_id"
            cursor.execute(new_order_query, {'test_id': test_id})
            result = cursor.fetchone()
            new_order_number = (result[0] if result[0] is not None else 0) + 1

            cursor.execute("SELECT TEST_STEPS_SEQ.NEXTVAL FROM dual")
            new_id = cursor.fetchone()[0] 

            sql = "INSERT INTO TEST_STEPS (ID, TEST_ID, NAME, ORDERNUMBER, STATUS, TYPE, SQL_CODE, TARGET_USER) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)"
            data = (new_id, test_id, new_step_name, new_order_number, 'ADDED', step_type, sql_code, target_user)

            cursor.execute(sql, data)
            connection.commit()

            return jsonify({'success': True, 'redirect_url': url_for('edit_steps', test_id=test_id)})
        finally:
            cursor.close()
            connection.close()

    except oracledb.Error as error:
        return jsonify({'success': False, 'error': str(error)})
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)})



@app.route('/delete_step', methods=['POST'])
def delete_step():
    try:
        id = request.form['id']
        test_id = request.form['test_id'] 
        connection = pool.acquire()
        cursor = connection.cursor()

        sql = "DELETE FROM TEST_STEPS WHERE ID = :id"
        cursor.execute(sql, {'id': id})
        connection.commit()
        cursor.close()

        return redirect(url_for('edit_steps', test_id=test_id))

    except oracledb.Error as error:
        return f"Error deleting step: {error}"

@app.route('/get_names_for_module', methods=['POST'])
def get_names_for_module():
    selected_module = request.json['module']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT DISTINCT(NAME) FROM LM.INV_JOBS WHERE MODULE = :module order by name asc"
        cursor.execute(sql, {'module': selected_module})
        names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(names)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_types_for_module', methods=['POST'])
def get_types_for_module():
    selected_module = request.json['module']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT DISTINCT(TYPE) FROM LM.INV_MODULE WHERE MODULE = :module order by type asc"
        cursor.execute(sql, {'module': selected_module})
        types = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(types)
    except Exception as e:
        return json.dumps({'error': str(e)})


def run_test_async(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        v_run_id = cursor.callfunc('TEST_PACKAGE.TEST_RUNNER', oracledb.NUMBER, [test_id])

        connection.commit()
        cursor.close()

        print(f"Test started successfully! Run ID: {v_run_id}")

        return {'success': True, 'v_run_id': v_run_id}

    except oracledb.Error as error:
        print(f"Error running test: {error}")
        return {'success': False, 'error': str(error)}

@app.route('/run_test/<test_id>', methods=['POST'])
def run_test(test_id):
    result = run_test_async(test_id)
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Test started successfully!', 'v_run_id': result['v_run_id']})
    else:
        return jsonify({'success': False, 'error': result['error']}), 500


if __name__ == '__main__':
    app.run(debug=True)
