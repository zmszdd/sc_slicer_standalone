; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun token_is_non_standard () Bool)
(declare-fun fees_distributed_in_non_standard_token () Bool)
(declare-fun token_transfer_succeeds () Bool)
(declare-fun sweep_reverts () Bool)
(assert
 (= token_is_non_standard token_is_non_standard))
(assert
 (= fees_distributed_in_non_standard_token fees_distributed_in_non_standard_token))
(assert
 (= token_transfer_succeeds token_transfer_succeeds))
(assert
 (= sweep_reverts sweep_reverts))
(define-fun report_preconditions () Bool (and token_is_non_standard
     fees_distributed_in_non_standard_token
     token_transfer_succeeds))
(define-fun report_safety () Bool (=> (and token_is_non_standard
         fees_distributed_in_non_standard_token
         token_transfer_succeeds)
    (not sweep_reverts)))
(define-fun report_effects () Bool (and token_is_non_standard
     fees_distributed_in_non_standard_token
     token_transfer_succeeds
     (not (not sweep_reverts))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
