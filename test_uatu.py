from uatu.init import initialize_db, get_uatu_config
from uatu.database import get_pipeline
from uatu.cli.pipeline import get_diagram

sess = initialize_db('.uatu/uatu.db')
pipeline = get_pipeline(sess, file_lists=[['uatu/git.py', 'uatu/logger.py', 'uatu/__init__.py', 'uatu/run.py'], ['uatu/cli/base.py'], ['uatu/simple_test.py', 'uatu/cli/pipeline.py', 'uatu/cli/node.py']])
print(get_diagram(pipeline))