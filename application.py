import os
from flask          import Flask, flash, request, redirect, url_for, render_template, send_file, after_this_request, session
from data_input     import file_uploading, file_check, get_timestamp
from data_output    import processing_data
from data_tools     import relative_path
from archive        import push_to_online_mongo_db
import  time




# SETTINGS ---------------------------------------------------------------------
# INPUT DATA
upload_folder           = relative_path('static/data/data_input')
output_folder           = 'static/data/data_output'
dlload_folder           = relative_path(output_folder)
allowed_extensions      = set(['csv'])
max_file_size           = 2 * 1024 * 1024 #2 megabytes

# OUTPUT DATA
# input_fields_name     = ['row','date','q','rain','temp','ETP_dint','peff']
output_fields_name      = ['row','date','q','rain','temp','ETP_dint','peff','baseflow_1','baseflow_2','baseflow_3']




# MAIN APP ---------------------------------------------------------------------
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH']     = max_file_size
app.config['UPLOAD_FOLDER']          = upload_folder
app.secret_key                       = os.environ.get("SECRET_KEY")


@app.route('/')
def get_page_home():
    return render_template('index.html')
    

@app.route('/instructions')
def get_page_instructions():
    return render_template('instructions.html')

    
@app.route('/models')
def get_page_models():
    return render_template('models.html')


@app.route('/team')
def get_page_team():
    return render_template('team.html')

    
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    
    if request.method == 'POST':
        
        if file_check(allowed_extensions) : 
        
            input_full_path  = file_uploading(app)
            output_filename  = get_timestamp(input_full_path) + "__" + request.form['output_filename'] + '.csv'
            output_full_path = os.path.join(dlload_folder, output_filename)
        
            session['output_filename'] = output_filename
    
            return redirect(url_for('output_data_calculation',  input_full_path     = input_full_path, 
                                                                output_full_path    = output_full_path, 
                                                                output_filename     = output_filename   ))
        else:
            
            return redirect("/upload")
        
    return render_template('upload.html')
    

# ERROR HANDLING TO BE SOLVE -------   
@app.route('/output_data_calculation')
def output_data_calculation():
    
    processing_data(request.args['input_full_path'], request.args['output_full_path'], output_fields_name)
    os.remove(relative_path(request.args['input_full_path']))
    
    return redirect(url_for('display_charts', output_filename=request.args['output_filename']))


@app.route('/charts')
def display_charts():
    
    if 'output_filename' in session:
        data_source = os.path.join(output_folder, session['output_filename'])
        return render_template("charts_with_data.html", data_source = data_source)
        
    return render_template("charts_without_data.html")
    

# To be merged / included in '/charts'
@app.route('/charts-demo')
def display_charts_demo():
    
    demo_file_name = 'data_output_example.csv'
    data_source = os.path.join(output_folder, demo_file_name)
    return render_template("charts_with_demo_data.html", data_source = data_source)
    

@app.route('/DownloadOutputFile') 
def send_output_csv():
    return send_file(relative_path(request.args['data_source']), mimetype='text/csv', attachment_filename = request.args['data_source'].split("/")[-1], as_attachment=True)
    

@app.route('/DownloadInputExampleFile') 
def send_input_example_csv():
    return send_file(relative_path(request.args['data_source']), mimetype='text/csv', attachment_filename = request.args['data_source'].split("/")[-1], as_attachment=True)


@app.route('/archiveDataOnMongoDatabase') 
def archive():
    push_to_online_mongo_db(relative_path(request.args['data_source']), output_fields_name)
    # To let X seconds for the user to read the triggered modal.
    time.sleep(5)
    # Should go for AJAX to avoid rendering again the page.
    return redirect(url_for('display_charts', output_filename=request.args['data_source'].split("/")[-1]))
    
    
@app.route('/deleteFiles')
def delete_files():
    os.remove(relative_path(request.args['data_source']))
    session.clear()
    # To let X seconds for the user to read the triggered modal.
    time.sleep(5)
    return redirect("/")
    
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))

# ------------------------------------------------------------------------------