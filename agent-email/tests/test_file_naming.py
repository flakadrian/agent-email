from file_naming import sanitize_filename


def test_sanitize_filename_strips_filesystem_invalid_characters():
    assert sanitize_filename('a/b\\c:d*e?f"g<h>i|j') == "a_b_c_d_e_f_g_h_i_j"


def test_sanitize_filename_strips_graph_api_problematic_characters():
    # Live gegen OneDrive verifiziert: '#' und '%' im Dateinamen führen bei
    # pfadadressierten Graph-API-Uploads zu "400 Bad Request", auch wenn der
    # Wert URL-encodiert ist.
    assert sanitize_filename("Your receipt, PBC #2944-4936-4922") == "Your receipt, PBC _2944-4936-4922"
    assert sanitize_filename("100% fertig") == "100_ fertig"


def test_sanitize_filename_falls_back_when_empty():
    assert sanitize_filename("   ") == "ohne-betreff"
