; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfb477388_minted_tokens_accounted_in_index () Bool)
(declare-fun cfb477388_total_weight_is_zero () Bool)
(assert
 (= cfb477388_minted_tokens_accounted_in_index cfb477388_minted_tokens_accounted_in_index))
(assert
 (= cfb477388_total_weight_is_zero cfb477388_total_weight_is_zero))
(define-fun report_preconditions () Bool cfb477388_total_weight_is_zero)
(define-fun report_safety () Bool (=> cfb477388_total_weight_is_zero cfb477388_minted_tokens_accounted_in_index))
(define-fun report_effects () Bool (and cfb477388_total_weight_is_zero
     (not cfb477388_minted_tokens_accounted_in_index)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
