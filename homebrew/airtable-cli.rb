class AirtableCli < Formula
  include Language::Python::Virtualenv

  desc "CLI tool to interact with the full Airtable Web API"
  homepage "https://github.com/xavierlopez/airtable-cli"
  url "https://files.pythonhosted.org/packages/source/a/airtable-cli/airtable_cli-0.1.0.tar.gz"
  # Update sha256 after running: shasum -a 256 <downloaded.tar.gz>
  sha256 "REPLACE_WITH_SHA256_AFTER_PYPI_PUBLISH"
  license "MIT"

  depends_on "python@3.12"

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/source/c/certifi/certifi-2024.2.2.tar.gz"
    sha256 "0569859f96c99554fa13952ca077d4b4ec"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "0.1.0", shell_output("#{bin}/airtable --version")
    assert_match "auth", shell_output("#{bin}/airtable --help")
  end
end
