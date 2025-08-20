import pytest
from app.utils import escape_html, generate_article_id
from types import SimpleNamespace

def test_escape_html():
    assert escape_html("<b>Hello</b>") == "&lt;b&gt;Hello&lt;/b&gt;"
    assert escape_html("Let's go") == "Let's go"

def test_generate_article_id():
    # Test with an entry that has an 'id' attribute
    entry_with_id = SimpleNamespace(id='test_id_123', title='Test Title', published='2025-08-18', link='http://example.com/article1')
    assert generate_article_id(entry_with_id) == 'test_id_123'

    # Test with an entry that has a 'link' attribute but no 'id'
    entry_with_link = SimpleNamespace(title='Test Title', published='2025-08-18', link='http://example.com/article2')
    assert generate_article_id(entry_with_link) == 'http://example.com/article2'

    # Test with an entry that has neither 'id' nor 'link'
    entry_without_id_or_link = SimpleNamespace(title='Another Test Title', published='2025-08-18', link=None)
    expected_hash = '1c3b6c7c5b5c5e5f5d5b5c5e5f5d5b5c5e5f5d5b5c5e5f5d5b5c5e5f5d5b5c5e'
    assert len(generate_article_id(entry_without_id_or_link)) == 64