; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdf0395b2_usdm_never_burned_or_returned () Bool)
(declare-fun cdf0395b2_usdm_refund_path_available () Bool)
(declare-fun cdf0395b2_usdm_transferred_to_vault () Bool)
(declare-fun cdf0395b2_user_blacklisted_between_request_and_claim () Bool)
(assert
 (= cdf0395b2_usdm_never_burned_or_returned cdf0395b2_usdm_never_burned_or_returned))
(assert
 (= cdf0395b2_usdm_refund_path_available cdf0395b2_usdm_refund_path_available))
(assert
 (= cdf0395b2_usdm_transferred_to_vault cdf0395b2_usdm_transferred_to_vault))
(assert
 (= cdf0395b2_user_blacklisted_between_request_and_claim cdf0395b2_user_blacklisted_between_request_and_claim))
(define-fun report_preconditions () Bool (and cdf0395b2_usdm_transferred_to_vault
     cdf0395b2_user_blacklisted_between_request_and_claim))
(define-fun report_safety () Bool (=> cdf0395b2_usdm_never_burned_or_returned
    (=> (and cdf0395b2_usdm_transferred_to_vault
             cdf0395b2_user_blacklisted_between_request_and_claim)
        cdf0395b2_usdm_refund_path_available)))
(define-fun report_effects () Bool (and cdf0395b2_usdm_never_burned_or_returned
     cdf0395b2_usdm_transferred_to_vault
     cdf0395b2_user_blacklisted_between_request_and_claim
     (not cdf0395b2_usdm_refund_path_available)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
