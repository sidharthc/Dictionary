from fabric.api import task, run, local
from fabric import state
import os
import json
import boto
import time
from boto.s3.key import Key

CAPTURE = False
NEVER_FAIL = False

COVERAGE_ENABLED = False
PROJECT_PACKGE = 'hipappear'
# Replace bucket_name, application_name, environment_name
# with the correct values alloted for your project
BUCKET_NAME = 'hipappear'
FILE_NAME = 'build.zip'
APPLICATION_NAME = 'hipappear'
ENVIRONMENT_NAME = 'appear-webserver-dev'


def _ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def _execute(cmd):
    if NEVER_FAIL:
        cmd = '%s; echo "Done"' % cmd

    return local(cmd, capture=CAPTURE)

@task()
def docs_gen():
    '''Generates Documents. Picks sources from docs folder.'''
    local("bin/sphinxbuilder")


@task()
def uml_gen():
    '''Generates Package Dependency Diagrams. Assumes Graphviz.'''
    local('bin/pyreverse -p deps %s' % PROJECT_PACKGE)
    local('mv *.dot out/')
    _ensure_dir('out/docs')
    local('dot -Tpng out/packages_deps.dot -o out/docs/packages_deps.png')


@task()
def runserver():
    '''Runs Django Server on port 8000'''
    local("bin/django runserver 0.0.0.0:8000")

@task()
def lint_py():
    '''Reports PyLint Errors & Warnings for Python files'''
    return _execute('bin/pylint --rcfile=etc/lint.rc --output-format={0} {1}'
                    .format('text', PROJECT_PACKGE))


@task()
def lint_js():
    '''Reports JSLint Errors & Warnings for JavaScript files'''
    return _execute('bin/jshint --config=etc/jshint.json src/static/js')


@task()
def lint_css():
    '''Reports CSSLint Errors & Warnings for CSS files'''
    _execute('bin/csslint hipappear/templates/*')  # TODO: Add option to specify csslint.json


@task()
def coverage():
    '''Enables Coverage. Used for test targets'''
    global COVERAGE_ENABLED
    COVERAGE_ENABLED = True


@task()
def test_all():
    '''Runs All Tests in src and tests folders'''
    test()


@task()
def test_integration():
    '''Runs All Tests in tests/integration package'''
    test('integration')


@task()
def test_unit():
    '''Runs All Tests in tests/unit package'''
    test('unit')


@task
def test(package=''):
    '''Run Tests for the given package bin/fab test:<package>'''
    options = []
    options.append('--with-xunit')
    options.append('--xunit-file=out/xunit.xml')

    if COVERAGE_ENABLED:
        options.append('--with-coverage')
        options.append('--cover-html')
        options.append('--cover-xml')
        options.append('--cover-xml-file=out/coverage.xml')
        options.append('--cover-erase')
        options.append('--cover-html-dir=out/coverage')
        options.append('--cover-package=%s' % PROJECT_PACKGE)
        options.append('--cover-min-percentage=80')

    return _execute('nosetests tests/unit/base_unit.py {0}'.format(' '.join(options)))

@task()
def deploy_to_dev_environment():
    '''Beanstalk - Deploys to Dev Environment'''
    version = "build_" + str(int(time.time()))
    upload_to_s3(BUCKET_NAME, version, FILE_NAME)
    create_version(APPLICATION_NAME, version)
    update_environment(ENVIRONMENT_NAME, version)

@task()
def create_new_version(version):
    '''Beanstalk - Creates a build for the provided version'''
    upload_to_s3(BUCKET_NAME, version, FILE_NAME)
    create_version(APPLICATION_NAME, version)

def upload_to_s3(bucket_name, key, file_name):
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name, validate=False)
    k = Key(bucket)
    k.key = key
    k.set_contents_from_filename(file_name)


def create_version(application, version):
    beanstalk = boto.connect_beanstalk()
    beanstalk.create_application_version(application, version,
                                         s3_bucket=BUCKET_NAME,
                                         s3_key=version)

def update_environment(environment, version):
    beanstalk = boto.connect_beanstalk()
    beanstalk.update_environment(environment_name=environment,
                                 version_label=version)


@task()
def check():
    '''Runs all checks and reports as JSON and out/summary.html. Useful for CI.'''
    import xml.etree.ElementTree as ET
    state.output.everything = False
    global CAPTURE
    global NEVER_FAIL
    global COVERAGE_ENABLED
    COVERAGE_ENABLED = True
    CAPTURE = True
    NEVER_FAIL = True

    test_all()
    js_lint = lint_js().split('\n')
    py_lint = lint_py().split('\n')
    css_lint = lint_css()
    coverage = ET.parse(open('out/coverage.xml')).getroot().attrib
    tests = ET.parse(open('out/xunit.xml')).getroot().attrib

    summary = {
               '8. Py Errors': len(py_lint),
               '7. JS Errors': len(js_lint),
               '6. CSS Errors': len(css_lint.split('\n')) if css_lint else 'N/A',
               '5. Coverage': coverage.get('line-rate', '0'),
               '1. Tests': tests.get('tests', 'NA'),
               '2. Errors': tests.get('errors', 'NA'),
               '3. Failures': tests.get('failures', 'NA'),
               '4. Skip': tests.get('skip', 'NA'),
            }
    print json.dumps(summary, indent=4)

    ROW_MAPPER = lambda x: "<tr><td>{0}</td><td>{1}</td></tr>".format(x[0], x[1])
    rows = sorted(map(ROW_MAPPER, summary.items()))

    summary_file = open('out/summary.html', 'w')
    summary_file.write('''
        <h4 style="color:red;">Checks Failed. Please Fix.</h4>
        <table style="text-align:left; width:200px;" border="1">
            <tr><td><b>Metric</b></td><td><b>Value</b></td></tr>
            {0}
        </table>
    '''.format("\n".join(rows)))

    summary_file.close()
