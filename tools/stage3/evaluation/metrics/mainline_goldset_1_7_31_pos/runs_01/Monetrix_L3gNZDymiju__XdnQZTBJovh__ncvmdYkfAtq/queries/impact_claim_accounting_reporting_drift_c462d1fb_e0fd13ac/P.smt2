; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca471d560_accounting_misreported () Bool)
(declare-fun ca471d560_decimals_offset () Int)
(declare-fun ca471d560_erc4626_expected_share_decimals () Int)
(declare-fun ca471d560_reported_share_decimals () Int)
(declare-fun ca471d560_share_decimals_consistent () Bool)
(declare-fun ca471d560_usdm_decimals () Int)
(assert
 (= ca471d560_accounting_misreported ca471d560_accounting_misreported))
(assert
 (= ca471d560_decimals_offset ca471d560_decimals_offset))
(assert
 (= ca471d560_erc4626_expected_share_decimals ca471d560_erc4626_expected_share_decimals))
(assert
 (= ca471d560_reported_share_decimals ca471d560_reported_share_decimals))
(assert
 (= ca471d560_share_decimals_consistent ca471d560_share_decimals_consistent))
(assert
 (= ca471d560_usdm_decimals ca471d560_usdm_decimals))
(define-fun report_preconditions () Bool (and (= 6 ca471d560_usdm_decimals)
     (= 6 ca471d560_decimals_offset)
     (= 6 ca471d560_reported_share_decimals)
     ca471d560_share_decimals_consistent))
(define-fun report_safety () Bool (=> (= ca471d560_erc4626_expected_share_decimals
       (+ ca471d560_usdm_decimals ca471d560_decimals_offset))
    (= ca471d560_reported_share_decimals
       ca471d560_erc4626_expected_share_decimals)))
(define-fun report_effects () Bool (and (= ca471d560_erc4626_expected_share_decimals
        (+ ca471d560_usdm_decimals ca471d560_decimals_offset))
     ca471d560_share_decimals_consistent
     (not (= ca471d560_reported_share_decimals
             ca471d560_erc4626_expected_share_decimals))
     ca471d560_accounting_misreported
     ca471d560_accounting_misreported))
(assert report_preconditions)
(check-sat)
(get-model)
