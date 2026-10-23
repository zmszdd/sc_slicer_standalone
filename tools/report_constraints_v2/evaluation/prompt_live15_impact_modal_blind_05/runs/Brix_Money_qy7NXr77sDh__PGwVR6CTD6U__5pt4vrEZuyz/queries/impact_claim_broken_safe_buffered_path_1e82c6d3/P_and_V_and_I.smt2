; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbfb0c30d_buffered_path_accepted () Bool)
(declare-fun cbfb0c30d_fee_buffer_bps_configured () Bool)
(declare-fun cbfb0c30d_msg_value_includes_buffer () Bool)
(assert
 (= cbfb0c30d_buffered_path_accepted cbfb0c30d_buffered_path_accepted))
(assert
 (= cbfb0c30d_fee_buffer_bps_configured cbfb0c30d_fee_buffer_bps_configured))
(assert
 (= cbfb0c30d_msg_value_includes_buffer cbfb0c30d_msg_value_includes_buffer))
(define-fun report_preconditions () Bool (and cbfb0c30d_fee_buffer_bps_configured cbfb0c30d_msg_value_includes_buffer))
(define-fun report_safety () Bool (=> (and cbfb0c30d_fee_buffer_bps_configured
         cbfb0c30d_msg_value_includes_buffer)
    cbfb0c30d_buffered_path_accepted))
(define-fun report_effects () Bool (and cbfb0c30d_fee_buffer_bps_configured
     cbfb0c30d_msg_value_includes_buffer
     (not cbfb0c30d_buffered_path_accepted)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
