; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3a40c530_buffered_path_accepted () Bool)
(declare-fun c3a40c530_fee_buffer_configured_flag () Bool)
(declare-fun c3a40c530_reliability_feature_delivered () Bool)
(declare-fun c3a40c530_user_sends_fee_plus_buffer_flag () Bool)
(assert
 (= c3a40c530_buffered_path_accepted c3a40c530_buffered_path_accepted))
(assert
 (= c3a40c530_fee_buffer_configured_flag c3a40c530_fee_buffer_configured_flag))
(assert
 (= c3a40c530_reliability_feature_delivered c3a40c530_reliability_feature_delivered))
(assert
 (= c3a40c530_user_sends_fee_plus_buffer_flag c3a40c530_user_sends_fee_plus_buffer_flag))
(define-fun report_preconditions () Bool (and c3a40c530_fee_buffer_configured_flag
     c3a40c530_user_sends_fee_plus_buffer_flag))
(define-fun report_safety () Bool (=> (and c3a40c530_fee_buffer_configured_flag
         c3a40c530_user_sends_fee_plus_buffer_flag)
    (and c3a40c530_buffered_path_accepted
         c3a40c530_reliability_feature_delivered)))
(define-fun report_effects () Bool (and c3a40c530_fee_buffer_configured_flag
     c3a40c530_user_sends_fee_plus_buffer_flag
     (not (and c3a40c530_buffered_path_accepted
               c3a40c530_reliability_feature_delivered))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
