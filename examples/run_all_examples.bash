EXAMPLES_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
MOLER_REPO_DIR="$( cd $EXAMPLES_DIR/.. >/dev/null && pwd )"

for file in `find $EXAMPLES_DIR -name "*.py" -print`
do
    echo "**********************************************************************************"
    echo "*"
    echo "*  RUNNING: $file"
    echo "*"
    echo "**********************************************************************************"
    # OLD_PYTHONPATH
    export PYTHONPATH=$MOLER_REPO_DIR
    python3.6 $file
    unset PYTHONPATH
    echo
done
