import pytest
import demistomock as demisto
import datetime

from AWS_SecurityHub import AWSClient, get_findings_command, fetch_incidents, list_members_command

FILTER_FIELDS_TEST_CASES = [
    (
        'some non parseable input',
        {}
    ),
    (
        'name=name,value=value,comparison=comparison',
        {
            'name': [{
                'Value': 'value',
                'Comparison': 'COMPARISON'
            }]
        }
    ),
    (
        'name=name1,value=value1,comparison=comparison1;name=name2,value=value2,comparison=comparison2',
        {
            'name1': [{
                'Value': 'value1',
                'Comparison': 'COMPARISON1'
            }],
            'name2': [{
                'Value': 'value2',
                'Comparison': 'COMPARISON2'
            }]
        }
    )
]


@pytest.mark.parametrize('test_input, expected_output', FILTER_FIELDS_TEST_CASES)
def test_parse_filter_field(test_input, expected_output):
    """
    Given:
        - A string that represents filter fields with the structure 'name=...,value=...,comparison=...;name=...' etc.
    When:
     - Parsing it into a dict

    Then:
     - Ensure unparseable string returns an empty dict
     - Ensure one set of name,value,comparison is parsed correctly
     - Ensure two sets of name,value,comparison are parsed correctly
    """
    from AWS_SecurityHub import parse_filter_field
    assert parse_filter_field(test_input) == expected_output


TAG_FIELDS_TEST_CASES = [
    (
        'some non parseable input',
        []
    ),
    (
        'key=key,value=value',
        [{
            'Key': 'key',
            'Value': 'value'
        }]
    ),
    (
        'key=key1,value=value1;key=key2,value=value2',
        [
            {
                'Key': 'key1',
                'Value': 'value1'
            },
            {
                'Key': 'key2',
                'Value': 'value2'
            },
        ]
    )
]


@pytest.mark.parametrize('test_input, expected_output', TAG_FIELDS_TEST_CASES)
def test_parse_tag_field(test_input, expected_output):
    """
    Given:
        - A string that represents tag fields with the structure 'key=...,value=...;key=...,value...' etc.
    When:
     - Parsing it into a list of keys and values

    Then:
     - Ensure unparseable string returns an empty list
     - Ensure one pair of key, value is parsed correctly
     - Ensure two pairs of key, value are parsed correctly
    """
    from AWS_SecurityHub import parse_tag_field
    assert parse_tag_field(test_input) == expected_output


RESOURCE_IDS_TEST_CASES = [
    ('a,b,c', ['a', 'b', 'c']),
    ('a, b, c', ['a', 'b', 'c']),
    ('', [])
]


@pytest.mark.parametrize('test_input, expected_output', RESOURCE_IDS_TEST_CASES)
def test_parse_resource_ids(test_input, expected_output):
    """
    Given:
        - A string that represent a list of ids.
    When:
     - Parsing it into a list

    Then:
     - Ensure empty string returns an empty list
     - Ensure a string without spaces return a valid list separated by ','.
     - Ensure a string with spaces return a valid list separated by ','.
    """
    from AWS_SecurityHub import parse_resource_ids
    assert parse_resource_ids(test_input) == expected_output


FINDINGS = [{
    'ProductArn': 'Test',
    'Description': 'Test',
    'SchemaVersion': '2021-05-27',
    'CreatedAt': '2020-03-22T13:22:13.933Z',
    'Id': 'Id',
    'Severity': {
        'Normalized': 0,
    },
}]


class MockClient:

    def get_findings(self, **kwargs):
        return {'Findings': FINDINGS}


def test_aws_securityhub_get_findings_command():
    """
    Given:
        - A dictionary that represents response body of aws_securityhub_get_findings API call without pagination -
        i.e doesn't have 'NextToken' key.
    When:
        - Running get_findings_command
    Then:
        - Verify returned value is as expected - i.e the findings list.
    """
    client = MockClient()
    human_readable, outputs, findings = get_findings_command(client, {})
    expected_output = FINDINGS

    assert findings == expected_output


def test_fetch_incidents(mocker):
    """
    Given:
        - A finding to fetch as incident with created time 2020-03-22T13:22:13.933Z
    When:
        - Fetching finding as incident
    Then:
        - Verify the last run is set as the created time + 1 millisecond, i.e. 2020-03-22T13:22:13.934Z
    """
    mocker.spy(demisto, 'setLastRun')
    client = MockClient()
    fetch_incidents(client, 'Low', False, None)
    assert demisto.setLastRun.call_args[0][0]['lastRun'] == '2020-03-22T13:22:13.934000+00:00'


def test_list_members_command(mocker):
    """
    Given:
        - mock aws_session
    When:
        - Running list_members_command
    Then:
        - Ensure that the command was executed correctly. In particular, ensure that the datetime fields are convereted to str.
    """
    aws_client = AWSClient("reg", "", "", 900, "p", "mock_aws_access_key_id", "mock_aws_secret_access_key", "", "", 3)
    client = aws_client.aws_session(service='securityhub', region="reg", role_arn='roleArnroleArnroleArn',
                                    role_session_name='roleSessionName')
    time_val = datetime.datetime(2022, 1, 1, 12, 0, 0, 0)
    mock_response = {'ResponseMetadata': 'mock_ResponseMetadata', 'Members': [{'UpdatedAt': time_val, 'InvitedAt': time_val}]}
    mocker.patch.object(client, 'list_members', return_value=mock_response)
    _, _, response = list_members_command(client, {})
    time_val_iso_format = time_val.isoformat()
    assert response == {'Members': [{'UpdatedAt': time_val_iso_format, 'InvitedAt': time_val_iso_format}]}
    assert type(response['Members'][0]['UpdatedAt']) == str
