import pytest

from ckanext.scheming.helpers import scheming_dataset_schemas


@pytest.mark.ckan_config('ckan.plugins', 'scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestTransmuteAction():
    def test_get_all_dataset_schemas(self):
        schemas = scheming_dataset_schemas()
        
        assert len(schemas) == 1
        assert 'dataset' in schemas
        
