import imageio, tempfile, shutil
        from pathlib import Path

        chars = len(sentence)
        if chars == 0:
            st.warning("Please enter some text.")
            st.stop()

        fps = 30
        total_frames = 6 * fps
        chars_per_frame = chars / total_frames

        # temp directory for PNG frames
        tmpdir = Path(tempfile.mkdtemp())
        progress = st.progress(0)

        for frm in range(total_frames):
            n = int(round(chars_per_frame * (frm + 1)))
            n = min(n, chars)
            img_rgb = frame(sentence[:n])[:, :, ::-1]          # BGR → RGB
            imageio.imwrite(tmpdir / f"{frm:05d}.png", img_rgb)
            if frm % 10 == 0:
                progress.progress(frm / total_frames)

        progress.empty()

        # ---- assemble MP4 with imageio-ffmpeg ----
        out_mp4 = tmpdir / "typing.mp4"
        with imageio.get_writer(out_mp4, fps=fps, codec="libx264", pix_fmt="yuv420p") as w:
            for frm in range(total_frames):
                w.append_data(imageio.imread(tmpdir / f"{frm:05d}.png"))

        # ---- download button ----
        with open(out_mp4, "rb") as f:
            st.download_button(
                label="⬇️ Download MP4",
                data=f,
                file_name="typing.mp4",
                mime="video/mp4"
            )
        st.success("MP4 ready – right-click → save, or use the button above.")

        # tidy up
        shutil.rmtree(tmpdir)
