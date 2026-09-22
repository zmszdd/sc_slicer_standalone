; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun offset18 () Int)
(declare-fun user_has_deposit () Bool)
(declare-fun full_withdrawal_attempted () Bool)
(declare-fun full_withdrawal_covers_entire_deposit () Bool)
(declare-fun withdrawal_reverts () Bool)
(assert
 (= offset18 offset18))
(assert
 (= user_has_deposit user_has_deposit))
(assert
 (= full_withdrawal_attempted full_withdrawal_attempted))
(assert
 (= full_withdrawal_covers_entire_deposit full_withdrawal_covers_entire_deposit))
(assert
 (= withdrawal_reverts withdrawal_reverts))
(define-fun report_preconditions () Bool (and (> 1000000000 offset18)
     user_has_deposit
     full_withdrawal_covers_entire_deposit))
(define-fun report_safety () Bool (=> full_withdrawal_attempted (not withdrawal_reverts)))
(define-fun report_effects () Bool (and full_withdrawal_attempted withdrawal_reverts))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
