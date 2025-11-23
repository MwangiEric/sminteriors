# Smart Preview
if 'ai_copy' in st.session_state and 'smart_layout' in st.session_state:
    if uploaded:
        st.subheader("🎬 Smart Preview")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("👀 Show Smart Layout", use_container_width=True):
                preview = create_preview(
                    product_img, 
                    st.session_state.ai_copy, 
                    price, 
                    phone, 
                    st.session_state.smart_layout
                )
                st.image(preview, use_column_width=True, caption="AI-Optimized Layout")

        with col2:
            if st.button("🚀 Create TikTok Video", type="primary", use_container_width=True):
                with st.status("Creating TikTok video..."):
                    video_path = create_tiktok_video(
                        product_img,
                        st.session_state.ai_copy,
                        price,
                        phone,
                        st.session_state.smart_layout
                    )

                    if video_path:
                        st.video(video_path)
                        with open(video_path, "rb") as f:
                            st.download_button(
                                "📥 Download TikTok Video", 
                                f, 
                                "tiktok_video.mp4", 
                                "video/mp4",
                                use_container_width=True
                            )
                        os.unlink(video_path)  # Delete video after download
else:
    st.error("Please generate AI Copy and Smart Layout before previewing.")
