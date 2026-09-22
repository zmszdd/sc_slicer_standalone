; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun offset18 () Int)
(declare-fun has_deposit () Bool)
(declare-fun withdrawal_reverts () Bool)
(assert
 (= offset18 offset18))
(assert
 (= has_deposit has_deposit))
(assert
 (= withdrawal_reverts withdrawal_reverts))
(define-fun report_preconditions () Bool (and (> 1000000000 offset18) (> 1000000000000000000 offset18) has_deposit))
(define-fun report_safety () Bool (=> (> 1000000000 offset18) (not withdrawal_reverts)))
(define-fun report_effects () Bool (and (> 1000000000 offset18) withdrawal_reverts))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
