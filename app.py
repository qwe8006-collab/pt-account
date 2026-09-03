# 회원 관리 탭 내 회원 이름 클릭 시 이력 및 메모 모달/아코디언 노출 로직
with c_name:
    if st.button(f"👤 {m['name']} 회원님", key=f"btn_detail_{m_id}_{idx}"):
        st.session_state["selected_detail_member_id"] = m_id if st.session_state.get("selected_detail_member_id") != m_id else None
        rerun()

# 선택된 회원의 상세 통합 이력 뷰어
if st.session_state.get("selected_detail_member_id") == m_id:
    st.markdown("---")
    st.markdown(f"#### 🔍 '{m['name']}' 회원의 통합 상세 정보 & 수업 이력")
    
    # 1. 특이사항 메모 수정란
    memo_val = st.text_area("💬 특이사항 메모", value=str(m.get("memo") or ""), key=f"detail_memo_{m_id}")
    if st.button("💾 메모 저장", key=f"save_detail_memo_{m_id}", type="primary"):
        members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "memo"] = str(memo_val)
        save_members(members)
        st.toast("메모가 저장되었습니다.")
        rerun()

    # 2. 역대 수업 진행 이력 타임라인
    st.markdown("##### 📜 진행된 수업 이력")
    m_logs = logs[pd.to_numeric(logs["member_id"], errors="coerce") == m_id].sort_values("date", ascending=False)
    if m_logs.empty:
        st.caption("진행된 수업 기록이 없습니다.")
    else:
        for _, l_row in m_logs.iterrows():
            st.markdown(f"""
            <div style="background:#F8FAFC; border-left:4px solid #2563EB; border-radius:8px; padding:10px 14px; margin-bottom:6px;">
                <b>📅 {l_row['date']} ({l_row.get('start_time','-')} ~ {l_row.get('end_time','-')})</b><br/>
                <span style="font-size:13px; color:#334155;">✔ 잘한점: {l_row.get('good_points','-')}</span><br/>
                <span style="font-size:13px; color:#334155;">✔ 보완점: {l_row.get('improve_points','-')}</span>
            </div>
            """, unsafe_allow_html=True)
