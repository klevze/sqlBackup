# Contributing to sqlBackup

Thank you for considering contributing to **sqlBackup**! We welcome all kinds of contributions — bug reports, feature requests, documentation improvements, and code contributions.

## 🛠️ Getting Started

1. **Fork the Repository**  
   Click the **Fork** button on GitHub and clone your fork:
   ```bash
   git clone https://github.com/your-username/sqlBackup.git
   cd sqlBackup
   ````

2. **Set Up the Environment**
   Install dependencies:

   ```bash
   pip3 install -r requirements.txt
   ```

   (Optional for development)

   ```bash
   pip3 install -r requirements-dev.txt
   pip3 install -e .
   ```

3. **Run Tests**
   Make sure existing tests pass:

   ```bash
   python3 -m unittest discover tests
   ```

4. **Validate Configuration**
   Test config files with the validation tool:

   ```bash
   python validate_config.py --config config.ini
   ```

## ✨ How to Contribute

### 🔍 Reporting Bugs

* Use [Issues](https://github.com/klevze/sqlBackup/issues) to report bugs.
* Include:

  * Clear title and description
  * Steps to reproduce the issue
  * Expected vs actual behavior
  * Logs or screenshots if applicable

### 💡 Suggesting Enhancements

* Open a new issue with:

  * A descriptive title
  * Clear explanation of the feature
  * Why it would be useful
  * Optional: suggested implementation

### 🧑‍💻 Submitting Code

* Create a new branch:

  ```bash
  git checkout -b feature/my-feature
  ```

* Follow PEP8 and the project's coding style.

* Write tests for new functionality.

* Run all tests and linters before committing.

* Commit using clear and meaningful messages:

  ```
  feat: Add S3 upload support
  fix: Correct config validator path issue
  docs: Update README with new install method
  ```

* Push to your fork and open a **Pull Request**.

### 📚 Improving Documentation

* Fix typos, clarify instructions, or add new examples.
* Update `docs/`, `README.md`, or `config.ini.default`.

## 🧪 Testing

* All features should be tested via `unittest` or a compatible framework.
* Tests are located in the `tests/` directory.
* Add tests for new modules or changes where possible.

## 🧾 Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) to keep this project welcoming and inclusive.

## 💬 Contact

If you have questions, open an issue or reach out via [GitHub Discussions](https://github.com/klevze/sqlBackup/discussions) (if enabled).

---

Happy backing up! 🚀
