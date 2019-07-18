import json
from uatu.core.orm import Pipeline
from uatu.core.init import initialize_db, get_uatu_config
from uatu.core.database import get_file, get_all_files, get_pipeline, get_all_pipelines

sess = initialize_db(get_uatu_config()["database_file"])


def test_add_pipeline():
    file_lists = [[__file__], [__file__], [__file__]]
    get_pipeline(sess, file_lists=file_lists, create=True)

    file_id = get_file(sess, file_path=__file__, create=False).id
    file_id_lists = [[file_id], [file_id], [file_id]]
    result = (
        sess.query(Pipeline).filter_by(file_id_lists=json.dumps(file_id_lists)).first()
    )
    assert not result is None