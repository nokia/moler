from pytest import mark, raises

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'


@mark.parametrize("path2cmds", ["moler/cmd"])
def test_documentation_exists(path2cmds):
    from moler.util.cmds_doc import check_if_documentation_exists
    assert check_if_documentation_exists(path2cmds) is True
