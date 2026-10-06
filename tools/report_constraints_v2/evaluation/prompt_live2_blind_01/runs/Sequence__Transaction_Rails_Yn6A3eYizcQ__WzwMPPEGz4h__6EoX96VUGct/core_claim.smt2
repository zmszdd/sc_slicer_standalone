; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun domain_separator_immutable () Bool)
(declare-fun chainid_changed () Bool)
(declare-fun contract_non_upgradeable () Bool)
(declare-fun recover_failed () Bool)
(assert
 (= domain_separator_immutable domain_separator_immutable))
(assert
 (= chainid_changed chainid_changed))
(assert
 (= contract_non_upgradeable contract_non_upgradeable))
(assert
 (= recover_failed recover_failed))
(define-fun report_preconditions () Bool (and domain_separator_immutable chainid_changed contract_non_upgradeable))
(define-fun report_safety () Bool (=> (and domain_separator_immutable chainid_changed contract_non_upgradeable)
    (not recover_failed)))
(define-fun report_effects () Bool (and domain_separator_immutable
     chainid_changed
     contract_non_upgradeable
     (not (not recover_failed))))
