# /usr/bin/zsh

echo "Running quality assurance checks..."
echo "=============================="
echo "Running Black..."
black .
echo "Running iSort..."
isort .
echo "Running Ruff..."
ruff check . --unsafe-fixes
echo "All checks passed successfully!"
