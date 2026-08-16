"""
Example tool template (DOM-01). Tools must export run() and optional TOOL_META.
This template uses safe imports so it won't crash if core.unit_converter isn't present yet.
"""
TOOL_META = {
    'title': 'Orifice Plate Flowmeter (Template)',
    'domain': 'DOM-01',
    'key': 'dom_01_hydraulics.orifice_plate'
}


def run():
    try:
        import streamlit as st
    except Exception:
        print('streamlit not available in this context; run() expects Streamlit runtime')
        return

    st.header('Orifice Plate Flowmeter (Template)')
    unit_system = st.session_state.get('unit_system', 'SI')
    if unit_system == 'Imperial':
        d_default = 4.0
        d_label = 'Pipe ID (inch)'
    else:
        d_default = 0.1023
        d_label = 'Pipe ID (m)'

    d = st.number_input(d_label, value=d_default)
    beta = st.number_input('Beta ratio', value=0.6, min_value=0.2, max_value=0.75)

    if st.button('Calculate'):
        # Placeholder calculation
        Q = 1.0 * d * beta  # dummy
        st.metric('Volumetric flow', f"{Q:.3g}")
        with st.expander('Intermediate values'):
            st.write({'Re': '---', 'Cd': '---'})
        st.download_button('Download CSV', data='flow,1\n', file_name='orifice_result.csv')
